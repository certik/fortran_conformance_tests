struct attr_pair { int first; int second; };
extern struct attr_pair attr_bind_common;
void c_set_common(int a, int b) { attr_bind_common.first = a; attr_bind_common.second = b; }
void c_get_common(int *a, int *b) { *a = attr_bind_common.first; *b = attr_bind_common.second; }
