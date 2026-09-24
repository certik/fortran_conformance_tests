program expr_conditional_syntax_forms
  implicit none
  integer :: checks, i, x
  checks=0
  x = (.true. ? 3 : 4)
  if (x /= 3) error stop 'ER1002:two-arm'
  checks=checks+1
  x = (.false. ? 3 : .true. ? 5 : 6)
  if (x /= 5) error stop 'ER1002:chain'
  checks=checks+1
  i = 1
  x = (i == 1 ? 7 : 8)
  if (x /= 7) error stop 'ER1002:scalar-guard'
  checks=checks+1
  if (checks /= 3) error stop 'ER1002:checks'
  write(*,'(a)') 'EXPRESSIONS CONDITIONAL SYNTAX FORMS OK'
end program expr_conditional_syntax_forms
