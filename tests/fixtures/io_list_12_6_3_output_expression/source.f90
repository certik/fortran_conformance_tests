program io_list_output_expression
  implicit none
  integer :: checks, x
  character(len=4) :: out
  checks = 0
  x = 6
  out = '####'
  write(out,'(SS,I2)') x + 4
  if (out /= '10  ') error stop 'output expression'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 OUTPUT_EXPRESSION OK'
end program io_list_output_expression
