! rule: S7.3.2.3-008
! covers: intrinsic-declared-kind-length
! evidence: effect
program dynamic_nonpolymorphic_intrinsic
    implicit none
    integer, parameter :: double_kind = kind(0.0d0)
    integer :: whole = 7
    real(double_kind) :: number = 0.0_double_kind
    character(len=4) :: text = 'reed'
    integer :: seen = -1
    call inspect(whole, seen)
    if (seen /= 1) error stop 'integer-result'
    seen = -1
    call inspect(number, seen)
    if (seen /= 2) error stop 'real-result'
    seen = -1
    call inspect(text, seen)
    if (seen /= 3) error stop 'character-result'
contains
    subroutine inspect(x, observed)
        class(*), intent(in) :: x
        integer, intent(out) :: observed
        observed = -1
        select type (x)
        type is (integer)
            if (x /= 7) error stop 'integer-payload'
            if (kind(x) /= kind(0)) error stop 'integer-kind'
            observed = 1
        type is (real(kind=double_kind))
            if (x /= 0.0_double_kind) error stop 'real-payload'
            if (kind(x) /= double_kind) error stop 'real-kind'
            observed = 2
        type is (character(len=*))
            if (len(x) /= 4) error stop 'character-length'
            if (x /= 'reed') error stop 'character-payload'
            observed = 3
        class default
            error stop 'nonpolymorphic-type-kind'
        end select
    end subroutine
end program
