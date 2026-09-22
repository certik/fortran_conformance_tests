! rule: S8.4-001
! covers: derived-explicit-override
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_derived_explicit_override_effect
  implicit none
  type :: sample
    integer :: component = -111
  end type sample
  type(sample) :: obj = sample(2719)
  integer :: checks
  checks=0
  if (obj%component /= 2719) then
    write(*,'(a)') 'INIT:derived_explicit_override:component-explicit-over-default'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'INIT:derived_explicit_override:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION DERIVED EXPLICIT OVERRIDE OK'
end program initialization_derived_explicit_override_effect
