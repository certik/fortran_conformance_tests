program enum_type_end_enum
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator :: before_end = 6, after_value
  end enum
  checks = 0
  if (after_value /= 7) then
    write(*,'(a)') 'ETY:end_enum:closed-definition-value'
    error stop
  end if
  checks = checks + 1
  if (checks /= 1) then
    write(*,'(a)') 'ETY:end_enum:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE R763 END ENUM OK'
end program enum_type_end_enum
