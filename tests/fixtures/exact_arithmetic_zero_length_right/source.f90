! rule: S10.1.5.3.1-002
! covers: zero-length-right
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_zero_length_right
  implicit none
  integer :: checks
  character(len=4) :: left
  character(len=0) :: right
  checks=0
  left = 'L0xP'
  right = ''
  ! The right operand length is 0, so 'L0xP' // '' has length 4+0=4 and value 'L0xP'.
  if (len(right) /= 0) then
    write(*,'(a)') 'EAF:zero_length_right:zero-right-right-length'
    error stop
  end if
  checks=checks+1
  if (len(left // right) /= 4) then
    write(*,'(a)') 'EAF:zero_length_right:zero-right-result-length'
    error stop
  end if
  checks=checks+1
  if (left // right /= 'L0xP') then
    write(*,'(a)') 'EAF:zero_length_right:zero-right-result-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'EAF:zero_length_right:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC ZERO LENGTH RIGHT OK'
end program exact_arithmetic_zero_length_right
