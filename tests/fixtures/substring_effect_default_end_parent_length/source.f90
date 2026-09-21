program substring_default_end_parent_length_effect
  implicit none
  character(len=6) :: c
  integer :: checks
  checks=0
  c='abcdef'
  if (c(4:) /= 'def') then
    write(*,'(a)') 'SSE:default_end_parent_length:default-end-value'
    error stop
  end if
  checks=checks+1
  if (len(c(4:)) /= 3) then
    write(*,'(a)') 'SSE:default_end_parent_length:default-end-length'
    error stop
  end if
  checks=checks+1
  if (c(4:) /= c(4:6)) then
    write(*,'(a)') 'SSE:default_end_parent_length:default-end-explicit'
    error stop
  end if
  checks=checks+1
  c(6:6)='Z'
  if (c(4:) /= 'deZ') then
    write(*,'(a)') 'SSE:default_end_parent_length:default-end-mutated-last'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'SSE:default_end_parent_length:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING DEFAULT END PARENT LENGTH OK'
end program substring_default_end_parent_length_effect
