import asyncio
import argparse
from eeg_music.server.WebServer import WebServer

async def run_api_server_only():
    """启动仅提供API服务的Web服务器，不需要硬件连接"""
    print("启动API服务器（无硬件模式）...")
    
    # 创建WebServer实例
    webserver = WebServer()
    
    try:
        # 直接运行HTTP服务器，不需要Arduino和Mindwave读取器
        await webserver.run(arduino_reader=None, mindwave_reader=None)
    except KeyboardInterrupt:
        print("\nAPI服务器已停止。")
    except Exception as e:
        print(f"\n启动API服务器时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='启动API服务器（无硬件模式）')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器地址 (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5500, help='HTTP端口 (default: 5500)')
    args = parser.parse_args()
    
    print(f"API服务器将在 http://{args.host}:{args.port} 启动")
    print("文件列表API: http://{args.host}:{args.port}/api/files")
    print("静态文件服务: http://{args.host}:{args.port}/")
    print("历史记录页面: http://{args.host}:{args.port}/history.html")
    print("\n按 Ctrl+C 停止服务器")
    
    asyncio.run(run_api_server_only())

if __name__ == "__main__":
    main() 