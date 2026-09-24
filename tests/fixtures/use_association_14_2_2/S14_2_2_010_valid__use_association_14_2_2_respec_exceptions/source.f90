! rule: S14.2.2-010
! covers: use-associated-public-private-exception use-associated-asynchronous-volatile-exception
! evidence: effect
! standard: f2023
! oracle-basis: standard
module respec_provider
  implicit none
  integer :: shared = 42
end module
module respec_attr_provider
  implicit none
  integer :: attr_shared = 42
end module
module respec_reexporter
  use respec_provider, only: shared
  implicit none
  private :: shared
  public :: read_shared
contains
  integer function read_shared()
    read_shared = shared
  end function
end module
program respec_exceptions
  implicit none
  integer :: checks
  checks = 0
  call check_private(checks)
  call check_async_volatile(checks)
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RESPEC EXCEPTIONS OK'
contains
  subroutine check_private(checks)
    use respec_reexporter, only: read_shared
    implicit none
    integer, intent(inout) :: checks
    if (read_shared() /= 42) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_async_volatile(checks)
    use respec_attr_provider, only: async_shared => attr_shared, vol_shared => attr_shared
    implicit none
    asynchronous :: async_shared
    volatile :: vol_shared
    integer, intent(inout) :: checks
    if (async_shared + vol_shared /= 84) error stop 2
    checks = checks + 1
  end subroutine
end program
