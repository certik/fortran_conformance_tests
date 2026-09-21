program substring_first_expression_start_effect
  implicit none
  character(len=6) :: c
  integer :: f, seed, checks
  checks=0
  c='abcdef'
  seed=1
  f=seed+2
  if (c(f:5) /= 'cde') then
    write(*,'(a)') 'SSE:first_expression_start:start-three'
    error stop
  end if
  checks=checks+1
  f=f-1
  if (c(f:5) /= 'bcde') then
    write(*,'(a)') 'SSE:first_expression_start:start-two'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'SSE:first_expression_start:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING FIRST EXPRESSION START OK'
end program substring_first_expression_start_effect
