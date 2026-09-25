program io_list_read_n_then_slice
  implicit none
  integer :: checks
  character(len=7) :: rec
  integer :: n, a(4)
  checks = 0
  rec = '3 5 6 7'
  n = -303
  a = [-41, -42, -43, -44]
  if (n /= -303) error stop 'n pre-read sentinel'
  checks = checks + 1
  if (any(a /= [-41, -42, -43, -44])) error stop 'a pre-read sentinel'
  checks = checks + 1
  read(rec,*) n, a(1:n)
  if (n /= 3) error stop 'n read before later bound'
  checks = checks + 1
  if (any(a /= [5, 6, 7, -44])) error stop 'slice values'
  checks = checks + 1
  if (checks /= 4) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 READ_N_THEN_SLICE OK'
end program io_list_read_n_then_slice
