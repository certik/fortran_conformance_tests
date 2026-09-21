program substring_default_start_one_effect
  implicit none
  character(len=6) :: c
  integer :: checks
  checks=0
  c='abcdef'
  if (c(:3) /= 'abc') then
    write(*,'(a)') 'SSE:default_start_one:default-start-value'
    error stop
  end if
  checks=checks+1
  if (c(:3) /= c(1:3)) then
    write(*,'(a)') 'SSE:default_start_one:default-start-explicit'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'SSE:default_start_one:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING DEFAULT START ONE OK'
end program substring_default_start_one_effect
