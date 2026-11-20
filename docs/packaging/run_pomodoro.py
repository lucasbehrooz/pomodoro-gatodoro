"""Ponto de entrada usado pelo PyInstaller para gerar o executável.

Mantido fora do pacote para que o import absoluto ``pomodoro`` funcione
quando o script é empacotado.
"""

from pomodoro.__main__ import main

if __name__ == "__main__":
    main()
