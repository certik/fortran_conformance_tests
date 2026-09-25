program io_list_implied_do_increment
  implicit none
  integer :: checks
  character(len=5) :: rec
  integer :: a(5), j, lo, hi, stride
  checks = 0
  rec = '8 9 7'
  a = [-1, -2, -3, -4, -5]
  lo = 1
  hi = 5
  stride = 2
  if (any(a /= [-1, -2, -3, -4, -5])) error stop 'a pre-read sentinel'
  checks = checks + 1
  read(rec,*) (a(j), j = lo + 1, hi, stride)
  if (any(a /= [-1, 8, -3, 9, -5])) error stop 'increment positions'
  checks = checks + 1
  if (checks /= 2) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 IMPLIED_DO_INCREMENT OK'
end program io_list_implied_do_increment
