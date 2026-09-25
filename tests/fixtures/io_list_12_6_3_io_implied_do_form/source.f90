program io_list_io_implied_do_form
  implicit none
  integer :: checks, i
  integer :: a(2), b(2)
  character(len=8) :: out
  checks = 0
  a = [1, 2]
  b = [3, 4]
  out = '########'
  write(out,'(SS,4I1)') (a(i), b(i), i = 1, 2)
  if (out /= '1324    ') error stop 'implied do form'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 IO_IMPLIED_DO_FORM OK'
end program io_list_io_implied_do_form
