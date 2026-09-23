program enum_type_constant_initializers
  implicit none
  integer, parameter :: seed = 4
  integer :: checks
  enum, bind(c)
    enumerator :: first = seed, second
    enumerator implicit_tail
  end enum
  checks = 0
  if (first /= 4) then
    write(*,'(a)') 'ETY:constant_initializers:prior-parameter-value'
    error stop
  end if
  checks = checks + 1
  if (second /= 5) then
    write(*,'(a)') 'ETY:constant_initializers:implicit-after-parameter'
    error stop
  end if
  checks = checks + 1
  if (implicit_tail /= 6) then
    write(*,'(a)') 'ETY:constant_initializers:implicit-initializer-admission'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'ETY:constant_initializers:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE R762 CONSTANT INITIALIZERS OK'
end program enum_type_constant_initializers
