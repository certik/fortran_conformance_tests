! rule: S8.4-005
! covers: subprogram-retention
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_subprogram_retention_effect
  implicit none
  integer :: first, second, checks
  checks=0
  call visit(first)
  call visit(second)
  if (first /= -31417) then
    write(*,'(a)') 'INIT:subprogram_retention:first-snapshot'
    error stop
  end if
  checks=checks+1
  if (second /= -31416) then
    write(*,'(a)') 'INIT:subprogram_retention:second-snapshot'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'INIT:subprogram_retention:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION SUBPROGRAM RETENTION OK'
contains
  subroutine visit(out)
    implicit none
    integer, intent(out) :: out
    integer :: kept = -31417
    out = kept
    kept = kept + 1
  end subroutine visit
end program initialization_subprogram_retention_effect
