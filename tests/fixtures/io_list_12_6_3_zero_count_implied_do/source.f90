program io_list_zero_count_implied_do
  implicit none
  integer :: checks, i
  integer :: vals(2)
  character(len=2) :: out
  checks = 0
  vals = [8, 9]
  out = '##'
  write(out,'(SS,I2,I2)') (vals(i), i = 1, 0), 7
  if (out /= ' 7') error stop 'zero-count implied-do marker'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 ZERO_COUNT_IMPLIED_DO OK'
end program io_list_zero_count_implied_do
