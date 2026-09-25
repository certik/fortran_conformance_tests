program io_list_io_implied_do_objects
  implicit none
  integer :: checks, i
  character(len=3) :: rec
  character(len=4) :: out
  integer :: a(2)
  checks = 0
  rec = '5 6'
  a = [-5, -6]
  out = '####'
  if (any(a /= [-5, -6])) error stop 'a pre-read sentinel'
  checks = checks + 1
  read(rec,*) (a(i), i = 1, 2)
  if (any(a /= [5, 6])) error stop 'input object form'
  checks = checks + 1
  write(out,'(SS,2I2)') (a(i) + 1, i = 1, 2)
  if (out /= ' 6 7') error stop 'output object form'
  checks = checks + 1
  if (checks /= 3) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 IO_IMPLIED_DO_OBJECTS OK'
end program io_list_io_implied_do_objects
