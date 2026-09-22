! rule: S10.1.5.3.1-003
! covers: left-grouped-concatenation-value
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_left_grouped_concatenation_value
  implicit none
  integer :: checks
  character(len=1) :: first
  character(len=2) :: second
  character(len=3) :: third
  checks=0
  first = 'A'
  second = 'bc'
  third = 'D3e'
  ! ('A' // 'bc') // 'D3e' has length (1+2)+3=6 and value 'AbcD3e'.
  if (len((first // second) // third) /= 6) then
    write(*,'(a)') 'EAF:left_grouped_concatenation_value:left-grouped-length'
    error stop
  end if
  checks=checks+1
  if ((first // second) // third /= 'AbcD3e') then
    write(*,'(a)') 'EAF:left_grouped_concatenation_value:left-grouped-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EAF:left_grouped_concatenation_value:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC LEFT GROUPED CONCATENATION VALUE OK'
end program exact_arithmetic_left_grouped_concatenation_value
