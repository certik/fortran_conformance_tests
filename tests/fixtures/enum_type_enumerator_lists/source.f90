program enum_type_enumerator_lists
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator plain_a, plain_b
    enumerator :: explicit_c = 5, explicit_d
  end enum
  checks = 0
  if (plain_b /= 1) then
    write(*,'(a)') 'ETY:enumerator_lists:colon-free-list-order'
    error stop
  end if
  checks = checks + 1
  if (explicit_d /= 6) then
    write(*,'(a)') 'ETY:enumerator_lists:colon-present-list-successor'
    error stop
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'ETY:enumerator_lists:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE R761 ENUMERATOR LISTS OK'
end program enum_type_enumerator_lists
