program enum_type_enum_def_structure
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator solo
  end enum
  enum, bind(c)
    enumerator :: anchor = 3
    enumerator follower
  end enum
  checks = 0
  if (solo /= 0) then
    write(*,'(a)') 'ETY:enum_def_structure:single-definition-value'
    error stop
  end if
  checks = checks + 1
  if (follower /= 4) then
    write(*,'(a)') 'ETY:enum_def_structure:multiple-statement-successor'
    error stop
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'ETY:enum_def_structure:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE R759 ENUM DEF STRUCTURE OK'
end program enum_type_enum_def_structure
