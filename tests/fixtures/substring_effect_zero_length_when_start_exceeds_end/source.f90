program substring_zero_length_when_start_exceeds_end_effect
  implicit none
  character(len=6) :: c
  integer :: checks
  checks=0
  c='abcdef'
  if (len(c(4:3)) /= 0) then
    write(*,'(a)') 'SSE:zero_length_when_start_exceeds_end:zero-length'
    error stop
  end if
  checks=checks+1
  if (c(4:3) /= '') then
    write(*,'(a)') 'SSE:zero_length_when_start_exceeds_end:zero-length-value'
    error stop
  end if
  checks=checks+1
  if (c /= 'abcdef') then
    write(*,'(a)') 'SSE:zero_length_when_start_exceeds_end:parent-unchanged'
    error stop
  end if
  checks=checks+1
  if (c(3:4) /= 'cd') then
    write(*,'(a)') 'SSE:zero_length_when_start_exceeds_end:neighbor-nonzero'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'SSE:zero_length_when_start_exceeds_end:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING ZERO LENGTH WHEN START EXCEEDS END OK'
end program substring_zero_length_when_start_exceeds_end_effect
