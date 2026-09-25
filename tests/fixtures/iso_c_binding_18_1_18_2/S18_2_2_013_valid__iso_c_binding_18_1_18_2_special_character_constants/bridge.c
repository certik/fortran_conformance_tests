int batch310_check_chars(char nul, char alert, char back, char form, char newline, char carriage, char tab, char vertical) {
  return (nul == '\0' && alert == '\a' && back == '\b' && form == '\f' && newline == '\n' && carriage == '\r' && tab == '\t' && vertical == '\v') ? 8 : -8;
}
