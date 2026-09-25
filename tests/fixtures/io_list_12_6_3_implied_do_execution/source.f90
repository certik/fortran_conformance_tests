program io_list_implied_do_execution
  implicit none
  integer :: checks, i
  integer :: a(3)
  character(len=5) :: rec
  checks = 0
  rec = '1 2 3'
  a = [-1, -2, -3]
  if (any(a /= [-1, -2, -3])) error stop 'a pre-read sentinel'
  checks = checks + 1
  read(rec,*) (a(i), i = 1, 3)
  if (any(a /= [1, 2, 3])) error stop 'implied-do execution values'
  checks = checks + 1
  if (i /= 4) error stop 'implied-do execution final variable'
  checks = checks + 1
  if (checks /= 3) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 IMPLIED_DO_EXECUTION OK'
end program io_list_implied_do_execution
