import subprocess
import sys
import os
import json
import secrets
import shutil
from pathlib import Path


def run_simulation():
    """
    启动 freqtrade 模拟交易
    """
    try:
        # 获取当前文件所在目录的绝对路径
        current_dir = Path(__file__).parent.absolute()
        config_path = current_dir / "user_data" / "config_price-act_strategy.json"

        if not config_path.exists():
            print(f"错误：配置文件不存在: {config_path}")
            return False

        # 读取配置文件并更新用户名密码 / token
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        def _is_placeholder(val: object) -> bool:
            """判断配置值是否为空或占位符。"""
            if val is None:
                return True
            if isinstance(val, str):
                s = val.strip()
                if not s:
                    return True
                # 常见占位符模式
                if s.startswith("${") and s.endswith("}"):
                    return True
                if "your_" in s and s.endswith("_here"):
                    return True
            return False

        def _gen_token(nbytes: int = 48) -> str:
            """生成高强度随机 token（URL safe）。"""
            return secrets.token_urlsafe(nbytes)

        # 更新 API 服务器配置
        api_cfg = config_data.get('api_server', {})

        # 仅当环境变量存在时才覆盖用户名密码，避免写入 None/空值
        _u = os.getenv('FREQTRADE_USERNAME')
        _p = os.getenv('FREQTRADE_PASSWORD')
        if _u:
            api_cfg['username'] = _u
        else:
            # 若当前配置为占位/空，则自动生成用户名
            cur_user = api_cfg.get('username')
            if _is_placeholder(cur_user):
                gen_user = f"user_{secrets.token_hex(4)}"
                api_cfg['username'] = gen_user
                print(f"已自动生成 api_server.username: {gen_user}")

        if _p:
            api_cfg['password'] = _p
        else:
            # 若当前配置为占位/空，则自动生成强密码
            cur_pass = api_cfg.get('password')
            if _is_placeholder(cur_pass):
                gen_pass = secrets.token_urlsafe(16)
                api_cfg['password'] = gen_pass
                print("已自动生成 api_server.password (请妥善保存)")
                print(f"当前密码: {gen_pass}")

        # 处理 JWT 秘钥：优先使用环境变量，否则在占位/空值时自动生成
        jwt_env = os.getenv('JWT_SECRET')
        if jwt_env:
            api_cfg['jwt_secret_key'] = jwt_env
        else:
            cur_jwt = api_cfg.get('jwt_secret_key')
            if _is_placeholder(cur_jwt):
                api_cfg['jwt_secret_key'] = _gen_token(48)
                print("已自动生成 jwt_secret_key")

        # 处理 WS token：优先使用环境变量，否则在占位/空值时自动生成
        ws_env = os.getenv('WS_TOKEN')
        if ws_env:
            api_cfg['ws_token'] = [ws_env]
        else:
            cur_ws = None
            if isinstance(api_cfg.get('ws_token'), list) and api_cfg.get('ws_token'):
                cur_ws = api_cfg['ws_token'][0]
            else:
                cur_ws = api_cfg.get('ws_token')
            if _is_placeholder(cur_ws):
                api_cfg['ws_token'] = [_gen_token(32)]
                print("已自动生成 ws_token")

        config_data['api_server'] = api_cfg

        # 写回配置文件
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        print(f"正在启动 freqtrade 模拟交易...")
        print(f"配置文件: {config_path}")
        print("按 Ctrl+C 停止交易")
        print("-" * 50)
        
        # 设置环境变量
        env = os.environ.copy()

        # 选择 Python 可执行文件：优先 sys.executable，退而求其次 python3/python
        python_exec = sys.executable or shutil.which("python3") or shutil.which("python")
        if not python_exec:
            raise RuntimeError("无法找到可用的 Python 解释器")

        # 构建命令（全部为字符串）
        cmd = [
            str(python_exec),  # 使用当前 Python 解释器
            "-m", "freqtrade", "trade",
            "--config", str(config_path),
            "--strategy", "PriceActionStrategy"
        ]
        
        # 设置环境变量（仅注入非空字符串）
        new_env_items = {
            # Binance API 配置
            "binance_API_KEY": os.getenv("BINANCE_API_KEY"),
            "binance_SECRET": os.getenv("BINANCE_API_SECRET"),

            # Freqtrade API 服务器配置
            "FREQTRADE_USERNAME": os.getenv("FREQTRADE_USERNAME"),
            "FREQTRADE_PASSWORD": os.getenv("FREQTRADE_PASSWORD"),
            "JWT_SECRET": os.getenv("JWT_SECRET"),
            "WS_TOKEN": os.getenv("WS_TOKEN"),
        }

        # 过滤 None / 空字符串，并确保值为 str
        filtered_env = {k: str(v) for k, v in new_env_items.items() if v is not None and str(v) != ""}
        if filtered_env:
            env.update(filtered_env)
        
        # 启动进程
        process = subprocess.Popen(
            cmd,
            cwd=str(current_dir),
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env  # 传递环境变量
        )
        
        # 等待进程结束
        process.wait()
        return True
        
    except KeyboardInterrupt:
        print("\n检测到中断信号，正在停止交易...")
        return False
    except Exception as e:
        print(f"启动模拟交易时出错: {e}")
        return False

def main():
    print("=" * 50)
    print("Freqtrade 模拟交易启动器")
    print("=" * 50)
    
    # 检查必要的依赖
    try:
        import freqtrade
        import dotenv
    except ImportError as e:
        print(f"错误：缺少必要的依赖: {e}")
        print("请使用以下命令安装所需依赖:")
        print("pip install python-dotenv freqtrade")
        if "freqtrade" in str(e):
            print("或者进入项目目录运行: pip install -e .")
        return
    
    # 启动模拟交易
    run_simulation()
    
    print("\n模拟交易已停止。")

if __name__ == "__main__":
    main()
