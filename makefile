DESKTOP_FILE = $(HOME)/Desktop/chat.desktop

install:
	@echo "[Desktop Entry]" > $(DESKTOP_FILE)
	@echo "Type=Application" >> $(DESKTOP_FILE)
	@echo "Terminal=true" >> $(DESKTOP_FILE)
	@echo "Name=chat" >> $(DESKTOP_FILE)
	@echo "Name[en_US]=chat" >> $(DESKTOP_FILE)
	@echo "Exec=$$(which python3) $(CURDIR)/chat.py" >> $(DESKTOP_FILE)
	@echo "Icon=$(CURDIR)/shortcut/chat.png" >> $(DESKTOP_FILE)
	@chmod +x $(DESKTOP_FILE)
	@echo "[*] installed in: \033[1;36m$(DESKTOP_FILE)\033[0m"
