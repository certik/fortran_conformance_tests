! rule: C1104
! covers: nonvariable-expression-selector-control, variable-selector-route-source-control
program ab_c1104_routes
  implicit none
  integer :: base, expr_seen, var_seen
  base=6; expr_seen=-1; var_seen=-2
  associate (expr_alias => base + 2)
    expr_seen=expr_alias
  end associate
  associate (var_alias => base)
    var_alias=18
  end associate
  var_seen=base
  if (expr_seen /= 8) then
    write(*,'(a)') 'C1104E'
    error stop
  end if
  if (var_seen /= 18) then
    write(*,'(a)') 'C1104V'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS C1104 ROUTES OK'

end program ab_c1104_routes
