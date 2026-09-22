! rule: S10.1.5.3.1-002
! covers: result-length-sum
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_result_length_sum
  implicit none
  integer :: checks
  character(len=2) :: left
  character(len=3) :: right
  checks=0
  left = 'mN'
  right = 'p8R'
  ! Operand lengths are 2 and 3, so LEN(left // right) must be 2+3=5.
  if (len(left // right) /= 5) then
    write(*,'(a)') 'EAF:result_length_sum:length-sum'
    error stop
  end if
  checks=checks+1
  if (left // right /= 'mNp8R') then
    write(*,'(a)') 'EAF:result_length_sum:length-sum-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EAF:result_length_sum:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC RESULT LENGTH SUM OK'
end program exact_arithmetic_result_length_sum
