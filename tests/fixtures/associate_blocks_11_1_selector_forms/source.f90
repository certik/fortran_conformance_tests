! rule: R1105
! covers: expression-selector-form, variable-selector-form
program ab_r1105_selector
  implicit none
  integer :: base, variable_result, expression_result
  base=9; variable_result=-1; expression_result=-2
  associate (expr_name => base + 4)
    expression_result=expr_name
  end associate
  associate (var_name => base)
    var_name=45
  end associate
  variable_result=base
  if (expression_result /= 13) then
    write(*,'(a)') 'EXPRFORM'
    error stop
  end if
  if (variable_result /= 45) then
    write(*,'(a)') 'VARFORM'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS R1105 SELECTOR OK'

end program ab_r1105_selector
