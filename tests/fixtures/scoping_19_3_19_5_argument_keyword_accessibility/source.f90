! rule: S19.3.5-002
! covers: argument-keyword-accessible-through-use-association
! covers: argument-keyword-accessible-through-host-association
module scoping_keyword_access_mod
  implicit none
  integer :: use_result = -801
  integer :: host_result = -802
contains
  subroutine used_proc(use_arg)
    integer, intent(in) :: use_arg
    use_result = use_arg
  end subroutine
  subroutine host_proc(host_arg)
    integer, intent(in) :: host_arg
    host_result = host_arg
  end subroutine
  subroutine host_caller()
    integer :: host_arg
    host_arg = -15
    call host_proc(host_arg=13)
  end subroutine
end module

program scoping_19_3_19_5_argument_keyword_accessibility
  use scoping_keyword_access_mod, only: used_proc, host_caller, use_result, host_result
  implicit none
  integer :: checks
  integer :: use_arg, host_arg
  checks = 0
  use_result = -904
  host_result = -905
  use_arg = -14
  host_arg = -15
  call used_proc(use_arg=12)
  call host_caller()
  if (use_result /= 12) then
    write(*,'(a)') 'SCOPE:argument_keyword_accessibility:use-associated-keyword'
    error stop
  end if
  checks = checks + 1
  if (use_arg /= -14) then
    write(*,'(a)') 'SCOPE:argument_keyword_accessibility:use-associated-sentinel'
    error stop
  end if
  checks = checks + 1
  if (host_result /= 13) then
    write(*,'(a)') 'SCOPE:argument_keyword_accessibility:host-associated-keyword'
    error stop
  end if
  checks = checks + 1
  if (host_arg /= -15) then
    write(*,'(a)') 'SCOPE:argument_keyword_accessibility:host-associated-sentinel'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:argument_keyword_accessibility:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 ARGUMENT KEYWORD ACCESSIBILITY OK'
contains
end program scoping_19_3_19_5_argument_keyword_accessibility
