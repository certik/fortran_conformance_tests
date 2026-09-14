! rule: S7.3.2.1-001
! covers: typeof-intrinsic-kind-length
! evidence: effect
! standard: f2023
program typeof_intrinsic_parameters
    implicit none
    integer, parameter :: rk = kind(0.0d0), ck = kind('a')
    real(rk) :: seed = 1.0d0
    character(kind=ck, len=3) :: label = 'abc'
    typeof(seed) :: value
    typeof(label) :: word
    value = 2.0d0
    word = 'XYZ'
    if (kind(value) /= rk) error stop 'real-kind'
    if (kind(word) /= ck .or. len(word) /= 3) error stop 'character-parameters'
    if (value /= 2.0d0 .or. word /= 'XYZ') error stop 'copies'
    if (seed /= 1.0d0 .or. label /= 'abc') error stop 'sources'
end program
