program pointer_data_basic
  implicit none
  integer, target :: t, v, u
  integer, pointer :: p
  integer :: checks
  checks = 0
  t = 17
  v = 41
  p => t
  if (.not. associated(p, t)) error stop
  checks = checks + 1
  if (p /= 17) error stop
  checks = checks + 1
  p = 19
  if (t /= 19) error stop
  checks = checks + 1
  p => u
  if (.not. associated(p, u)) error stop
  checks = checks + 1
  p = 23
  if (u /= 23) error stop
  checks = checks + 1
  if (checks /= 5) error stop
  print '(a)', 'POINTER DATA BASIC OK'
end program pointer_data_basic
