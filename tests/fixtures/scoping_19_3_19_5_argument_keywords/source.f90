! rule: S19.3.5-001
! covers: internal-module-interface-keyword-host-scope
! covers: procedure-declaration-keyword-containing-scope
module scoping_keyword_mod
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

subroutine interface_body_proc(iface_arg)
  implicit none
  integer, intent(in) :: iface_arg
  common /kw_iface_common/ iface_result
  integer :: iface_result
  iface_result = iface_arg
end subroutine

subroutine pointer_target(ptr_arg)
  implicit none
  integer, intent(in) :: ptr_arg
  common /kw_ptr_common/ ptr_result
  integer :: ptr_result
  ptr_result = ptr_arg
end subroutine

program scoping_19_3_19_5_argument_keywords
  use scoping_keyword_mod, only: used_proc, host_caller, use_result, host_result
  implicit none
  integer :: checks
  interface
    subroutine interface_body_proc(iface_arg)
      integer, intent(in) :: iface_arg
    end subroutine
    subroutine pointer_target(ptr_arg)
      integer, intent(in) :: ptr_arg
    end subroutine
  end interface
  abstract interface
    subroutine pointer_iface(ptr_arg)
      integer, intent(in) :: ptr_arg
    end subroutine
  end interface
  procedure(pointer_iface), pointer :: proc_ptr
  integer :: internal_result, alpha, iface_arg, ptr_arg, use_arg, host_arg
  integer :: iface_result, ptr_result
  common /kw_iface_common/ iface_result
  common /kw_ptr_common/ ptr_result
  checks = 0
  internal_result = -901
  iface_result = -902
  ptr_result = -903
  use_result = -904
  host_result = -905
  alpha = -11
  iface_arg = -12
  ptr_arg = -13
  use_arg = -14
  host_arg = -15
  proc_ptr => pointer_target
  call internal_proc(alpha=21)
  call interface_body_proc(iface_arg=31)
  call proc_ptr(ptr_arg=41)
  call used_proc(use_arg=12)
  call host_caller()
  if (internal_result /= 21) then
    write(*,'(a)') 'SCOPE:argument_keywords:internal-keyword'
    error stop
  end if
  checks = checks + 1
  if (alpha /= -11) then
    write(*,'(a)') 'SCOPE:argument_keywords:alpha-sentinel'
    error stop
  end if
  checks = checks + 1
  if (iface_result /= 31) then
    write(*,'(a)') 'SCOPE:argument_keywords:interface-keyword'
    error stop
  end if
  checks = checks + 1
  if (iface_arg /= -12) then
    write(*,'(a)') 'SCOPE:argument_keywords:interface-sentinel'
    error stop
  end if
  checks = checks + 1
  if (ptr_result /= 41) then
    write(*,'(a)') 'SCOPE:argument_keywords:procedure-declaration-keyword'
    error stop
  end if
  checks = checks + 1
  if (ptr_arg /= -13) then
    write(*,'(a)') 'SCOPE:argument_keywords:procedure-declaration-sentinel'
    error stop
  end if
  checks = checks + 1
  if (use_result /= 12) then
    write(*,'(a)') 'SCOPE:argument_keywords:use-associated-keyword'
    error stop
  end if
  checks = checks + 1
  if (use_arg /= -14) then
    write(*,'(a)') 'SCOPE:argument_keywords:use-associated-sentinel'
    error stop
  end if
  checks = checks + 1
  if (host_result /= 13) then
    write(*,'(a)') 'SCOPE:argument_keywords:host-associated-keyword'
    error stop
  end if
  checks = checks + 1
  if (host_arg /= -15) then
    write(*,'(a)') 'SCOPE:argument_keywords:host-associated-sentinel'
    error stop
  end if
  checks = checks + 1
  if (checks /= 10) then
    write(*,'(a)') 'SCOPE:argument_keywords:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 ARGUMENT KEYWORDS OK'
contains
  subroutine internal_proc(alpha)
    integer, intent(in) :: alpha
    internal_result = alpha
  end subroutine
end program scoping_19_3_19_5_argument_keywords
