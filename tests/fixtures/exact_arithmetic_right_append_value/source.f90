! rule: S10.1.5.3.1-002
! covers: right-append-value
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_right_append_value
  implicit none
  integer :: checks
  character(len=2) :: left
  character(len=3) :: right
  checks=0
  left = 'AB'
  right = 'q7Z'
  ! 'AB' // 'q7Z' is left followed by right: 'ABq7Z'; swapped order would be 'q7ZAB'.
  if (len(left // right) /= 5) then
    write(*,'(a)') 'EAF:right_append_value:right-append-length'
    error stop
  end if
  checks=checks+1
  if (left // right /= 'ABq7Z') then
    write(*,'(a)') 'EAF:right_append_value:right-append-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EAF:right_append_value:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC RIGHT APPEND VALUE OK'
end program exact_arithmetic_right_append_value
