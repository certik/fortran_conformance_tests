! rule: S10.1.5.3.1-003
! covers: nested-parentheses-value
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_nested_parentheses_value
  implicit none
  integer :: checks
  character(len=1) :: first
  character(len=2) :: second
  character(len=3) :: third
  checks=0
  first = 'u'
  second = 'V2'
  third = 'wx9'
  ! Nested parentheses do not change the final value: 'u' // ('V2' // 'wx9') = 'uV2wx9'.
  if (len((((first)) // ((second) // ((third))))) /= 6) then
    write(*,'(a)') 'EAF:nested_parentheses_value:nested-parentheses-length'
    error stop
  end if
  checks=checks+1
  if ((((first)) // ((second) // ((third)))) /= 'uV2wx9') then
    write(*,'(a)') 'EAF:nested_parentheses_value:nested-parentheses-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EAF:nested_parentheses_value:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC NESTED PARENTHESES VALUE OK'
end program exact_arithmetic_nested_parentheses_value
