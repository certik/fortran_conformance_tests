! rule: S11.1.3.1-001
! covers: associate-name-source-control, ...
program ab1131_purpose
  implicit none
  integer :: outer, target, expr_seen, var_seen
  outer=700; target=12; expr_seen=-1; var_seen=-2
  associate (outer => target, expr_alias => target + 5)
    outer=33
    expr_seen=expr_alias
    var_seen=outer
  end associate
  if (outer /= 700) then
    write(*,'(a)') 'OUTER'
    error stop
  end if
  if (target /= 33) then
    write(*,'(a)') 'TARGET'
    error stop
  end if
  if (expr_seen /= 17) then
    write(*,'(a)') 'EXPR'
    error stop
  end if
  if (var_seen /= 33) then
    write(*,'(a)') 'VAR'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS PURPOSE OK'

end program ab1131_purpose
