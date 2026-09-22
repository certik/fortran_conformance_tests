! rule: S10.1.5.3.1-002
! covers: zero-length-left
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_zero_length_left
  implicit none
  integer :: checks
  character(len=0) :: left
  character(len=3) :: right
  checks=0
  left = ''
  right = 'R9q'
  ! The left operand length is 0, so '' // 'R9q' has length 0+3=3 and value 'R9q'.
  if (len(left) /= 0) then
    write(*,'(a)') 'EAF:zero_length_left:zero-left-left-length'
    error stop
  end if
  checks=checks+1
  if (len(left // right) /= 3) then
    write(*,'(a)') 'EAF:zero_length_left:zero-left-result-length'
    error stop
  end if
  checks=checks+1
  if (left // right /= 'R9q') then
    write(*,'(a)') 'EAF:zero_length_left:zero-left-result-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'EAF:zero_length_left:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC ZERO LENGTH LEFT OK'
end program exact_arithmetic_zero_length_left
