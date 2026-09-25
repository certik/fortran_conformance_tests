program io_list_output_implied_do_object_control
  implicit none
  integer :: checks, i
  integer :: a(2)
  character(len=4) :: out
  checks = 0
  a = [7, 8]
  out = '####'
  write(out,'(SS,2I2)') (a(i), i = 1, 2)
  if (out /= ' 7 8') error stop 'output-list implied-do object'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 OUTPUT_IMPLIED_DO_OBJECT_CONTROL OK'
end program io_list_output_implied_do_object_control
