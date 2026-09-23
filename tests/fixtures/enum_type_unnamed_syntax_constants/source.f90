program enum_type_unnamed_syntax_constants
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator :: lower = 2, upper = 5
    enumerator extent_marker
  end enum
  integer :: table(lower:upper)
  integer :: vector(upper + extent_marker)
  checks = 0
  table = 37
  vector = 41
  if (lbound(table, 1) /= 2) then
    write(*,'(a)') 'ETY:unnamed_syntax_constants:array-lower-bound'
    error stop
  end if
  checks = checks + 1
  if (ubound(table, 1) /= 5) then
    write(*,'(a)') 'ETY:unnamed_syntax_constants:array-upper-bound'
    error stop
  end if
  checks = checks + 1
  if (size(vector) /= 11) then
    write(*,'(a)') 'ETY:unnamed_syntax_constants:array-size-from-two-enumerators'
    error stop
  end if
  checks = checks + 1
  if (table(upper) /= 37) then
    write(*,'(a)') 'ETY:unnamed_syntax_constants:table-sentinel'
    error stop
  end if
  checks = checks + 1
  if (vector(1) /= 41) then
    write(*,'(a)') 'ETY:unnamed_syntax_constants:vector-sentinel'
    error stop
  end if
  checks = checks + 1
  if (checks /= 5) then
    write(*,'(a)') 'ETY:unnamed_syntax_constants:check-total'
    error stop
  end if
  write(*,'(a)') 'ENUM TYPE NAMED CONSTANT CONSUMER OK'
end program enum_type_unnamed_syntax_constants
