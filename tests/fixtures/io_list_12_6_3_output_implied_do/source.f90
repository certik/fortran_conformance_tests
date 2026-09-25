program io_list_output_implied_do
  implicit none
  integer :: checks
  integer :: a(3), i
  character(len=6) :: out
  checks = 0
  a = [2, 4, 6]
  out = '######'
  write(out,'(SS,3I2)') (a(i) + 1, i = 1, 3)
  if (len(out) /= 6) error stop 'out len'
  checks = checks + 1
  if (out /= ' 3 5 7') error stop 'output implied-do values'
  checks = checks + 1
  if (checks /= 2) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 OUTPUT_IMPLIED_DO OK'
end program io_list_output_implied_do
