program substring_second_expression_end_effect
  implicit none
  character(len=6) :: c
  integer :: l, seed, checks
  checks=0
  c='abcdef'
  seed=2
  l=seed+2
  if (c(2:l) /= 'bcd') then
    write(*,'(a)') 'SSE:second_expression_end:end-four'
    error stop
  end if
  checks=checks+1
  l=l+1
  if (c(2:l) /= 'bcde') then
    write(*,'(a)') 'SSE:second_expression_end:end-five'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'SSE:second_expression_end:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING SECOND EXPRESSION END OK'
end program substring_second_expression_end_effect
