program enum_type_no_initializer_control
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator :: colon_a, colon_b
    enumerator bare_a, bare_b
  end enum
  checks = 0
  if (colon_b /= 1) then
    write(*,'(a)') 'ETY:no_initializer_control:colon-present-no-initializer'
    error stop
  end if
  checks = checks + 1
  if (bare_a /= 2) then
    write(*,'(a)') 'ETY:no_initializer_control:colon-free-no-initializer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'ETY:no_initializer_control:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE C7111 NO INITIALIZER CONTROL OK'
end program enum_type_no_initializer_control
