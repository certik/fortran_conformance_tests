program io_list_input_implied_do
  implicit none
  integer :: checks
  character(len=5) :: rec
  integer :: a(3), i
  checks = 0
  rec = '1 2 3'
  a = [-11, -22, -33]
  i = -44
  if (any(a /= [-11, -22, -33])) error stop 'a pre-read sentinel'
  checks = checks + 1
  read(rec,*) (a(i), i = 1, 3)
  if (any(a /= [1, 2, 3])) error stop 'implied-do item order'
  checks = checks + 1
  if (checks /= 2) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 INPUT_IMPLIED_DO OK'
end program io_list_input_implied_do
