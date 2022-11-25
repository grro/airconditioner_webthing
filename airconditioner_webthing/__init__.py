from airconditioner_webthing.app import App, ArgumentSpec
from airconditioner_webthing.airconditioner_webthing import run_server

def main():
    App.run(run_function=lambda args, desc: run_server(description=desc, port=args['port'], ip_address=args['ip'], id=int(args['id']), name=args['name']),
            packagename="airconditioner_webthing",
            arg_specs=[ArgumentSpec("ip", str, "the ip address", True),
                       ArgumentSpec("id", int, "the id", True),
                       ArgumentSpec("name", str, "the name", False, "")])

if __name__ == '__main__':
    main()
