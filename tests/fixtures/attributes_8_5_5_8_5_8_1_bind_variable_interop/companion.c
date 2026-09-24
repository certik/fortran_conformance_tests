extern int default_label_value;
extern int attr_bind_scalar;
extern int attr_bind_array[2];
void c_set_default(int v) { default_label_value = v; }
int c_get_default(void) { return default_label_value; }
void c_set_scalar(int v) { attr_bind_scalar = v; }
int c_get_scalar(void) { return attr_bind_scalar; }
void c_set_array(int i, int v) { attr_bind_array[i] = v; }
int c_get_array(int i) { return attr_bind_array[i]; }
