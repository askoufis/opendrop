from opendrop.app.app import App

from opendrop.shims import matplotlib_preloader

def main():
    app = App()

    def exit_handler():
        print("Exited.")

    app.on_exit.bind(exit_handler)

if __name__ == '__main__':
    main()
