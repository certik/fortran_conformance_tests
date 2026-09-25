program io_list_pointer_io
  implicit none
  integer :: checks
  character(len=2) :: rec
  character(len=4) :: out
  integer, target :: target
  integer, pointer :: p
  checks = 0
  rec = '31'
  out = '####'
  target = -919
  p => target
  if (.not. associated(p, target)) error stop 'pointer not associated before input'
  checks = checks + 1
  if (target /= -919) error stop 'target pre-read sentinel'
  checks = checks + 1
  read(rec,*) p
  if (target /= 31) error stop 'input pointer target value'
  checks = checks + 1
  target = 42
  write(out,'(SS,I2)') p
  if (len(out) /= 4) error stop 'out len'
  checks = checks + 1
  if (out /= '42  ') error stop 'output pointer target value'
  checks = checks + 1
  if (checks /= 5) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 POINTER_IO OK'
end program io_list_pointer_io
