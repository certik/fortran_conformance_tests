! rule: S11.1.3.3-004
! covers: optional-selector-present-control
program ab1133_optional_present
  implicit none
  integer :: observed
  observed=-1
  call use_optional(17, observed)
  if (observed /= 22) then
    write(*,'(a)') 'OPT'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS OPTIONAL PRESENT OK'

contains
  subroutine use_optional(arg, out)
    integer, optional, intent(in) :: arg
    integer, intent(out) :: out
    if (.not. present(arg)) error stop
    associate (alias => arg)
      out=alias+5
    end associate
  end subroutine use_optional
end program ab1133_optional_present
