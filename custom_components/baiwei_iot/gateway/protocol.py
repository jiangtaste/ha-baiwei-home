import logging
from typing import Optional, Set, Dict

logger = logging.getLogger(__name__)


class Protocol:
    DEFAULT_EXCLUDE_KEYS: Set[str] = {
        'api_version', 'from', 'to', 'msg_id',
        'msg_class', 'msg_name', 'msg_type', 'status'
    }
    CLIENT_SN = "hass-baiwei-iot"

    def __init__(self, client_sn=CLIENT_SN):
        """
        :param client_sn: 本设备客户端序列号
        """
        self.client_sn = client_sn
        self.gateway_sn = ""
        self.token: Optional[str] = None  # 登录后保存的 token

    async def update_token_from_response(self, message: dict) -> None:
        """
        尝试从登录响应中提取 token 并保存。
        """
        if "user" in message:
            self.token = message["user"].get("token")
            if self.token:
                logger.info(f"Token saved: {self.token}")
            else:
                logger.warning("No token found in login response")

    async def update_gateway_sn(self, gateway_sn: str):
        self.gateway_sn = gateway_sn

    def pack(
            self,
            path: str,
            payload: Dict
    ) -> Dict:
        """
        根据 path 和业务负载构造完整请求消息体。

        :param path: 格式为 "msg_class/msg_name" 的路径字符串
        :param payload: 业务数据字典
        :return: 合并后的完整消息字典
        """
        if "/" not in path:
            raise ValueError(f"Invalid path format: {path}, expected 'msg_class/msg_name'")

        msg_class, msg_name = path.split("/", 1)

        fields = {
            'api_version': '0.1',
            'from': self.client_sn,
            'to': self.gateway_sn,
            'msg_class': msg_class,
            'msg_name': msg_name,
            'msg_type': 'get'  # msg_id 在 connection 中插入
        }

        # 自动插入 token
        if self.token and "token" not in payload:
            payload = {**payload, "token": self.token}

        return {**fields, **payload}

    def unpack(
            self,
            data: Dict,
            exclude_keys: Optional[Set[str]] = None
    ) -> Dict:
        """
        从完整消息中提取业务字段，排除通用字段。

        会校验 from、to 字段是否匹配本实例的网关和客户端序列号，
        以及 status 是否为 0，否则返回空字典。

        :param data: 完整消息字典
        :param exclude_keys: 需要排除的字段集合，默认排除通用字段
        :return: 仅包含业务字段的字典
        """
        gateway_sn = data.get("from")

        # 校验时用“或”逻辑更合理，保证至少一方匹配，否则视为无效消息
        if self.gateway_sn and gateway_sn != self.gateway_sn:
            logger.warning(f"Invalid gateway_sn: expected {self.gateway_sn}, got {gateway_sn}")
            return {}

        status = data.get("status", 0)  # report 时无状态值，默认为0
        if status != 0:
            logger.warning(f"Invalid status: {status}")
            return {}

        if exclude_keys is None:
            exclude_keys = self.DEFAULT_EXCLUDE_KEYS

        return {k: v for k, v in data.items() if k not in exclude_keys}
