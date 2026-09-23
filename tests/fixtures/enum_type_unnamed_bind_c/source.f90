program enum_type_unnamed_bind_c
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator :: required = 8, observed
  end enum
  checks = 0
  if (observed /= 9) then
    write(*,'(a)') 'ETY:unnamed_bind_c:unnamed-bind-c-observed'
    error stop
  end if
  checks = checks + 1
  if (checks /= 1) then
    write(*,'(a)') 'ETY:unnamed_bind_c:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE R760 UNNAMED BIND C OK'
end program enum_type_unnamed_bind_c
