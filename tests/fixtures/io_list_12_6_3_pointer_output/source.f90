program io_list_pointer_output
  implicit none
  integer :: checks
  integer, target :: target
  integer, pointer :: p
  character(len=4) :: out
  checks = 0
  target = 54
  p => target
  out = '####'
  if (.not. associated(p, target)) error stop 'pointer not associated before output'
  checks = checks + 1
  write(out,'(SS,I2)') p
  if (out /= '54  ') error stop 'pointer output target'
  checks = checks + 1
  if (checks /= 2) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 POINTER_OUTPUT OK'
end program io_list_pointer_output
